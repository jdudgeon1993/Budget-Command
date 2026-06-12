
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_15b62b52b7853dc26eb8ab9d2cc8fc51 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_85d27e9aeefd218c061f729fb0e74aac = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.go_prev_month", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{"aria-label":"Previous month",css:({ ["cursor"] : "pointer", ["color"] : "#6868a2", ["padding"] : "6px 10px", ["borderRadius"] : "6px", ["fontSize"] : "15px", ["&:hover"] : ({ ["color"] : "#818cf8", ["background"] : "#1c1c25" }) }),onClick:on_click_85d27e9aeefd218c061f729fb0e74aac,role:"button",tabIndex:0},children)
    )
});
