
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_2774e0cad5158e061736a514ec04a529 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_639b1981bc47edf1e1997ed3d03ce750 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.reset_whatif", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "8px 14px", ["borderRadius"] : "8px", ["cursor"] : "pointer", ["fontSize"] : "12px", ["background"] : "#f8717118", ["color"] : "#f87171", ["border"] : "1px solid #f8717144", ["&:hover"] : ({ ["background"] : "#f8717128" }) }),onClick:on_click_639b1981bc47edf1e1997ed3d03ce750},children)
    )
});
