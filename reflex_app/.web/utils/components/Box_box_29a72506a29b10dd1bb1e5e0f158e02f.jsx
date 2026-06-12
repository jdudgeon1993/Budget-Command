
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_29a72506a29b10dd1bb1e5e0f158e02f = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_3491f026199f260863edb2ed8767ae51 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_add_account", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["letterSpacing"] : "0.08em", ["textTransform"] : "uppercase", ["padding"] : "9px 14px", ["borderRadius"] : "8px", ["border"] : "1px dashed #BF5AF255", ["color"] : "#BF5AF2", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["textAlign"] : "center", ["width"] : "100%", ["&:hover"] : ({ ["background"] : "#BF5AF20d" }) }),onClick:on_click_3491f026199f260863edb2ed8767ae51},children)
    )
});
